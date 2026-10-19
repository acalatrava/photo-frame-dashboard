"""Reads what Home HQ needs to know about an APK without any Android tooling: the package name, the version
and the fingerprint of the signing certificate."""
import hashlib
import io
import struct
import zipfile
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs7


class ApkError(ValueError):
    pass


@dataclass
class ApkInfo:
    package: str
    version_code: int
    version_name: str
    cert_sha256: str


_RES_XML = 0x0003
_RES_STRING_POOL = 0x0001
_RES_XML_START_ELEMENT = 0x0102
_UTF8_FLAG = 0x100
_TYPE_STRING = 0x03
_TYPE_INT_DEC = 0x10
_TYPE_INT_HEX = 0x11


def _read_pool(data: bytes, base: int) -> list[str]:
    _, header_size, _, count, _, flags, strings_start, _ = struct.unpack_from("<HHIIIIII", data, base)
    offsets = struct.unpack_from(f"<{count}I", data, base + header_size)
    utf8 = bool(flags & _UTF8_FLAG)
    out = []
    for off in offsets:
        pos = base + strings_start + off
        if utf8:
            # Two lengths (characters, then bytes), each one or two bytes long.
            pos += 2 if data[pos] & 0x80 else 1
            n = data[pos]
            pos += 1
            if n & 0x80:
                n = ((n & 0x7F) << 8) | data[pos]
                pos += 1
            out.append(data[pos:pos + n].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", data, pos)[0]
                pos += 2
            out.append(data[pos:pos + n * 2].decode("utf-16-le", "replace"))
    return out


def parse_manifest(data: bytes) -> tuple[str, int, str]:
    """Package, versionCode and versionName from a compiled (binary) AndroidManifest.xml."""
    try:
        kind, header_size, total = struct.unpack_from("<HHI", data, 0)
        if kind != _RES_XML:
            raise ApkError("AndroidManifest.xml no es un XML binario de Android")
        pos, strings = header_size, []
        while pos + 8 <= min(total, len(data)):
            ctype, _, csize = struct.unpack_from("<HHI", data, pos)
            if csize < 8:
                break
            if ctype == _RES_STRING_POOL:
                strings = _read_pool(data, pos)
                break
            pos += csize
        return _find_manifest_tag(data, strings)
    except (struct.error, IndexError) as exc:
        raise ApkError("No se pudo leer AndroidManifest.xml") from exc


def _find_manifest_tag(data: bytes, strings: list[str]) -> tuple[str, int, str]:
    pos = struct.unpack_from("<H", data, 2)[0]
    total = struct.unpack_from("<I", data, 4)[0]
    while pos + 8 <= min(total, len(data)):
        ctype, _, csize = struct.unpack_from("<HHI", data, pos)
        if csize < 8:
            break
        if ctype == _RES_XML_START_ELEMENT:
            # header (16 bytes) then: ns, name, attrStart, attrSize, attrCount, idIndex, classIndex, styleIndex
            ns, name, attr_start, attr_size, attr_count = struct.unpack_from("<iiHHH", data, pos + 16)
            if strings[name] != "manifest":
                raise ApkError("El primer elemento del manifiesto no es <manifest>")
            values: dict[str, object] = {}
            base = pos + 16 + attr_start
            for i in range(attr_count):
                _, a_name, raw, _, _, a_type, a_data = struct.unpack_from("<iiiHBBi", data, base + i * attr_size)
                key = strings[a_name]
                if raw != -1:
                    values[key] = strings[raw]
                elif a_type in (_TYPE_INT_DEC, _TYPE_INT_HEX):
                    values[key] = a_data
                elif a_type == _TYPE_STRING:
                    values[key] = strings[a_data]
            if "package" not in values or "versionCode" not in values:
                raise ApkError("El manifiesto no indica el paquete o el versionCode")
            return str(values["package"]), int(values["versionCode"]), str(values.get("versionName", ""))
        pos += csize
    raise ApkError("AndroidManifest.xml sin elemento <manifest>")


def signing_cert_sha256(zf: zipfile.ZipFile) -> str:
    """SHA-256 of the first signing certificate in the v1 (JAR) signature block, or '' when there is none.
    Android compares the same DER certificate when it decides whether an update is allowed."""
    for name in zf.namelist():
        upper = name.upper()
        if upper.startswith("META-INF/") and upper.rsplit(".", 1)[-1] in ("RSA", "DSA", "EC"):
            try:
                certs = pkcs7.load_der_pkcs7_certificates(zf.read(name))
            except ValueError:
                continue
            if certs:
                return hashlib.sha256(certs[0].public_bytes(serialization.Encoding.DER)).hexdigest()
    return ""


def inspect(data: bytes) -> ApkInfo:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ApkError("El archivo no es un APK válido") from exc
    with zf:
        if "AndroidManifest.xml" not in zf.namelist() or "classes.dex" not in zf.namelist():
            raise ApkError("El archivo no parece un APK de Android")
        package, code, name = parse_manifest(zf.read("AndroidManifest.xml"))
        return ApkInfo(package, code, name, signing_cert_sha256(zf))

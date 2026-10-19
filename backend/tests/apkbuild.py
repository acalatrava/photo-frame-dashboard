"""Builds tiny but structurally real APKs (binary AndroidManifest + signature block) for the update tests."""
import datetime
import io
import struct
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID


def new_identity(cn="Test"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650)).sign(key, hashes.SHA256()))
    return key, cert


def _pool(strings, utf8):
    data, offsets = b"", []
    for s in strings:
        offsets.append(len(data))
        if utf8:
            raw = s.encode()
            data += bytes([len(s), len(raw)]) + raw + b"\0"
        else:
            data += struct.pack("<H", len(s)) + s.encode("utf-16-le") + b"\0\0"
    data += b"\0" * (-len(data) % 4)
    start = 28 + 4 * len(strings)
    size = start + len(data)
    head = struct.pack("<HHIIIIII", 1, 28, size, len(strings), 0, 0x100 if utf8 else 0, start, 0)
    return head + b"".join(struct.pack("<I", o) for o in offsets) + data


def manifest(package, version_code, version_name, utf8=False):
    strings = ["versionCode", "versionName", "package", "manifest", package, version_name]
    pool = _pool(strings, utf8)
    attrs = [
        (-1, 2, 4, 3, 4),                      # package="..." (raw string)
        (-1, 0, -1, 0x10, version_code),      # versionCode (int)
        (-1, 1, 5, 3, 5),                      # versionName (raw string + typed string)
    ]
    body = b"".join(struct.pack("<iiiHBBi", ns, name, raw, 8, 0, typ, data) for ns, name, raw, typ, data in attrs)
    size = 36 + len(body)
    start = struct.pack("<HHIii", 0x102, 16, size, 1, -1) + struct.pack("<iiHHHHHH", -1, 3, 20, 20, 3, 0, 0, 0) + body
    xml = pool + start
    return struct.pack("<HHI", 3, 8, 8 + len(xml)) + xml


def build_apk(package="com.wesbos.homehq", version_code=7, version_name="2.4", identity=None, utf8=False, payload=b""):
    key, cert = identity or new_identity()
    sig = (pkcs7.PKCS7SignatureBuilder().set_data(b"manifest").add_signer(cert, key, hashes.SHA256())
           .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature]))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("AndroidManifest.xml", manifest(package, version_code, version_name, utf8))
        z.writestr("classes.dex", b"dex\n035\0" + payload)
        z.writestr("META-INF/CERT.RSA", sig)
    return out.getvalue(), cert

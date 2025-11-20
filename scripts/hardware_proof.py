#!/usr/bin/env python3
"""
hardware_proof.py
Cross-platform version of your capture + sign + EXIF-embed system.

Works on:
- Linux (Raspberry Pi + desktop)
- macOS
- Windows (Git Bash / CMD / PowerShell)
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime, timezone
import sys
import shutil
import subprocess


# Crypto
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Image / EXIF
from PIL import Image
import piexif

# Optional camera support (Linux only)
try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

# --------- Cross-platform path fix ----------
def fix_path(path: str) -> str:
    """Converts Windows backslashes → forward slashes, safe on all OS."""
    return os.path.abspath(path).replace("\\", "/")


### CONFIG ###
DEVICE_ID = "device-01"
PRIVATE_KEY_PATH = fix_path("device_private_key.pem")
PUBLIC_KEY_PATH  = fix_path("device_public_key.pem")
FIRMWARE = "cam-v1.0"
RAW_IMAGE_PATH = fix_path("capture.jpg")
FINAL_IMAGE_PATH = fix_path("capture_with_proof.jpg")
### END CONFIG ###


# --------- Key management ----------
def ensure_private_key():
    if os.path.exists(PRIVATE_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    key = ed25519.Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(pem)
    os.chmod(PRIVATE_KEY_PATH, 0o600)
    print("[+] Generated private key")
    return key


def export_public_key(privkey):
    pub = privkey.public_key()
    pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(pem)

    # Raw bytes for embedding
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return pem, raw


# --------- Capture photo (optional) ----------
def capture_photo(output_path):
    """
    Cross-platform camera capture:
    - Raspberry Pi: Picamera2
    - macOS: imagesnap (best), fallback to ffmpeg
    """

    # ---------------------
    # 1. Raspberry Pi Camera
    # ---------------------
    if Picamera2 is not None:
        picam = Picamera2()
        cfg = picam.create_still_configuration(main={"size": (1920, 1080)})
        picam.configure(cfg)
        picam.start()
        picam.capture_file(output_path)
        picam.stop()
        print(f"[+] Captured via Picamera2 -> {output_path}")
        return

    # ---------------------
    # 2. macOS Support
    # ---------------------
    if sys.platform == "darwin":

        # (A) Prefer imagesnap
        if shutil.which("imagesnap"):
            try:
                print("[+] Capturing using imagesnap...")
                subprocess.run(["imagesnap", output_path], check=True)
                print(f"[+] Captured using imagesnap -> {output_path}")
                return
            except subprocess.CalledProcessError as e:
                print("[!] imagesnap failed:", e)

        # (B) Fallback to ffmpeg (macOS built-in avfoundation camera API)
        if shutil.which("ffmpeg"):
            try:
                print("[+] Detecting macOS camera list...")
                device_list = subprocess.check_output(
                    ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                    stderr=subprocess.STDOUT,
                ).decode()

                # Parse first camera index
                cam_index = "0"  # default
                print(f"[+] Using camera index: {cam_index}")

                subprocess.run([
                    "ffmpeg",
                    "-f", "avfoundation",
                    "-i", cam_index,
                    "-frames:v", "1",
                    output_path
                ], check=True)

                print(f"[+] Captured using ffmpeg -> {output_path}")
                return

            except Exception as e:
                print("[!] ffmpeg capture failed:", e)

        print("[!] No working macOS capture tool found.")
        print("    Install with:")
        print("    brew install imagesnap")
        print("    OR:")
        print("    brew install ffmpeg")
        return

    # ---------------------
    # 3. Other platforms
    # ---------------------
    print("[!] No supported camera backend for this OS.")


# --------- Image hashing (EXIF-safe) ----------
def strip_exif_and_hash(image_path):
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        w, h = img_rgb.size
        pixel_data = img_rgb.tobytes()

    hsh = hashlib.sha256()
    hsh.update(f"{w}x{h}".encode())
    hsh.update(pixel_data)
    return hsh.hexdigest()


# --------- Canonical JSON payload ----------
def canonical_payload(d: dict) -> bytes:
    return json.dumps(d, separators=(",", ":"), sort_keys=True).encode()


# --------- Signing ----------
def create_and_sign_proof(privkey, device_id, image_hash, firmware, raw_pub):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    nonce = secrets.token_hex(16)

    proof = {
        "device_id": device_id,
        "timestamp": timestamp,
        "image_hash": image_hash,
        "nonce": nonce,
        "firmware": firmware,
        "sig_alg": "Ed25519",
        "public_key_b64": base64.b64encode(raw_pub).decode()
    }

    msg = canonical_payload(proof)
    signature = privkey.sign(msg)

    proof["signature"] = base64.b64encode(signature).decode()
    return proof


# --------- EXIF embed ----------
def embed_proof_into_exif(input_image_path: str, proof: dict, output_image_path: str):
    """
    Cross-platform EXIF writer:
    - macOS: Always uses 3-argument piexif.insert(...)
    - Linux: Tries binary insert then falls back
    - Windows: Uses 3-arg insert
    """
    proof_json = json.dumps(proof, separators=(',', ':'))
    
    try:
        exif_dict = piexif.load(input_image_path)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    exif_dict.setdefault("Exif", {})
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = proof_json.encode("utf-8")

    exif_bytes = piexif.dump(exif_dict)

    # ---- macOS & Windows: use the safe 3-arg insert() ----
    try:
        piexif.insert(exif_bytes, input_image_path, output_image_path)
        print(f"[+] Embedded proof using piexif 3-arg insert -> {output_image_path}")
        return
    except Exception as e:
        print("[!] 3-argument insert failed:", e)

    # ---- Linux fallback: binary insert ----
    try:
        with open(input_image_path, "rb") as f:
            jpeg_bytes = f.read()
        new_jpeg = piexif.insert(exif_bytes, jpeg_bytes)
        with open(output_image_path, "wb") as f:
            f.write(new_jpeg)
        print(f"[+] Embedded proof using binary mode -> {output_image_path}")
        return
    except Exception as e:
        print("[!] Binary insert failed:", e)

    # ---- Last fallback (lossy): Pillow re-encode ----
    from PIL import Image
    img = Image.open(input_image_path)
    img.save(output_image_path, "JPEG", exif=exif_bytes, quality=95)
    print(f"[+] Embedded using Pillow (re-encoded) -> {output_image_path}")


# --------- Verify ----------
def verify_embedded_proof(image_path):
    exif_dict = piexif.load(image_path)
    raw = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")
    proof = json.loads(raw.decode())

    # Check hash
    recomputed = strip_exif_and_hash(image_path)
    if recomputed != proof["image_hash"]:
        print("❌ HASH MISMATCH — image altered!")
        return False

    # Verify signature
    pub_raw = base64.b64decode(proof["public_key_b64"])
    signature = base64.b64decode(proof["signature"])
    payload = {k: proof[k] for k in proof if k != "signature"}
    msg = canonical_payload(payload)

    pub = ed25519.Ed25519PublicKey.from_public_bytes(pub_raw)

    try:
        pub.verify(signature, msg)
        print("✅ Signature OK — image authentic.")
        return True
    except Exception as e:
        print("❌ Signature invalid:", e)
        return False


# --------- MAIN FLOW ----------
def main():
    priv = ensure_private_key()
    pem, raw_pub = export_public_key(priv)

    try:
        capture_photo(RAW_IMAGE_PATH)
    except Exception as e:
        print("[!] Camera capture failed:", e)

    if not os.path.exists(RAW_IMAGE_PATH):
        sys.exit("❌ Missing input image at: " + RAW_IMAGE_PATH)

    image_hash = strip_exif_and_hash(RAW_IMAGE_PATH)
    print("[+] Image hash:", image_hash)

    proof = create_and_sign_proof(priv, DEVICE_ID, image_hash, FIRMWARE, raw_pub)
    embed_proof_into_exif(RAW_IMAGE_PATH, proof, FINAL_IMAGE_PATH)

    print("\nVerifying...")
    ok = verify_embedded_proof(FINAL_IMAGE_PATH)
    print("Result:", ok)


if __name__ == "__main__":
    main()

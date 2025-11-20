# Melon

A platform to help segregate real-world content from AI generated content using cryptographic embedded proofs and trusted hardware sources.

## Problem Statement

In an era of deepfakes, AI manipulation, and digital misinformation, proving the authenticity of visual content has become critical. Traditional image verification methods are easily circumvented by sophisticated editing tools, not scalable for real-time verification needs, lack cryptographic proof of origin and integrity, and don't provide device attestation for source validation.

Melon solves this by creating an immutable chain of trust from camera sensor to final verification.

## What is Melon?

Melon is a decentralized image verification platform that provides cryptographic proof of image authenticity through hardware attestation and blockchain technology. Our platform enables hardware device registration with economic staking mechanisms, cryptographic proof generation at point of capture, real-time verification of image authenticity, AI-generated content labeling with embedded proofs, and decentralized storage on 0G Network for permanent archival.

## Key Features

### Hardware Attestation
Device fingerprinting with unique hardware identifiers, Ed25519 cryptographic signatures for tamper-proof validation, and firmware version tracking with nonce-based replay protection.

### Real-time Verification
Sub-6 second average verification time with EXIF metadata analysis and integrity checking, plus cryptographic signature validation with public key verification.

### Tamper Detection
Advanced heuristics for detecting image manipulation, hash-based content integrity verification, and metadata stripping and recycling detection.

### Economic Security Model
0.01 ETH staking requirement for device registration, slashing mechanisms for malicious actors, and on-chain proof storage and verification.

### AI Content Verification
Embedded cryptographic proofs for AI-generated images, model attestation and generation metadata, and distinguishable AI vs hardware-captured content.

### Decentralized Storage
Integration with 0G Storage network, permanent immutable proof archival, and content-addressed storage with merkle proofs.

## Technology Stack

### Frontend
* Next.js 15.5.4 (React framework with App Router)
* Tailwind CSS 4 (Utility-first styling)
* RainbowKit 2.2.8 (Wallet connection interface)
* Wagmi 2.17.5 (Ethereum interactions)
* Three.js 0.170.0 (3D hardware visualization)

### Smart Contracts
* Solidity ^0.8.13 (Contract language)
* Foundry (Development framework)
* OpenZeppelin 5.4.0 (Security libraries)
* Ethereum Sepolia (Testnet deployment)

### Backend & Storage
* 0G Storage SDK 0.3.1 (Decentralized storage)
* Sharp 0.34.4 (Server-side image processing)
* Node.js Crypto (Cryptographic operations)

### Hardware Integration
* Python 3.9+ (Hardware proof generation)
* PiCamera2 (Raspberry Pi camera integration)
* PIL/Pillow (Image manipulation)
* Cryptography Library (Ed25519 signatures)

### AI Integration
* Google Gemini 2.5 Flash (Image generation)
* Vercel AI SDK 5.0.56 (LLM orchestration)

## Smart Contract Addresses

### Sepolia Testnet
**Contract Address:** 0x50302bdcc8dcb8ddbf5a09636ed9a22e05f65849  
**Staking Amount:** 0.01 ETH

### 0G Testnet
**Contract Address:** 0x66f0c4c9a21b78d4d92358d087176964982e1c21  
**Staking Amount:** 0.01 OG

### OG Mainnet
**Contract Address:** 0x66f0c4c9a21b78d4d92358d087176964982e1c21  
**Staking Amount:** 0.01 OG

## Setup and Running

> Note: We currently support Raspberry Pi5 machine based hardware

### Step 1: Hardware Setup

Run this command on the hardware:

```bash
./script/capture_and_embed.sh
```

This generates a Hardware UUID which is hardware specific. Our scripts generate Ed25519 compatible public and private keys for hardware and prevent malicious usage by staking tokens.

We create a payload with signature using the hardware based private key and encoded public key inside the hash and embed it into EXIF format for images before saving into JPG/PNG format.

We then verify the signature against the public key using Ed25519 scheme. We also use PKCS7 format with a forked version of zkPDF to further verify the payload itself and the hardware based certificate using RSA + SHA256 and ASN1 format.

### Step 2: Device Registration

Copy the hardware UUID and paste it on our platform and stake 0.01 tokens to whitelist the hardware as a trusted source of truth.

### Step 3: Fetch Captured Content

On your local machine, fetch the captured file using:

```bash
./scripts/fetch.sh
```

### Step 4: Verification

Upload the image on our portal to verify hardware details and ownership.

### Step 5: AI Playground

Explore our AI Playground to generate images with embedded proofs for our AI agents that create images with AI proof.

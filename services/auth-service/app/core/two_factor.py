import pyotp
import qrcode
import io
import base64
from typing import Tuple

class TwoFactorAuth:
    def __init__(self):
        pass
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def get_provisioning_uri(
        self,
        username: str,
        secret: str,
        issuer: str = "OpsCraft"
    ) -> str:
        """Get provisioning URI for QR code"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate QR code as base64 image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def get_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes"""
        import secrets
        return [secrets.token_hex(4) for _ in range(count)]

# Add 2FA routes
from fastapi import APIRouter, Depends, HTTPException

twofa_router = APIRouter()

@twofa_router.post("/enable")
async def enable_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable 2FA for user"""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    twofa = TwoFactorAuth()
    secret = twofa.generate_secret()
    provisioning_uri = twofa.get_provisioning_uri(current_user.username, secret)
    qr_code = twofa.generate_qr_code(provisioning_uri)
    backup_codes = twofa.get_backup_codes()
    
    # Store secret temporarily (user must verify before enabling)
    current_user.two_factor_secret = secret
    current_user.backup_codes = json.dumps(backup_codes)
    db.commit()
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "message": "Scan QR code with authenticator app and verify to complete setup"
    }

@twofa_router.post("/verify")
async def verify_two_factor_setup(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and complete 2FA setup"""
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    twofa = TwoFactorAuth()
    
    if not twofa.verify_token(current_user.two_factor_secret, token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    current_user.two_factor_enabled = True
    db.commit()
    
    return {"message": "2FA enabled successfully"}

@twofa_router.post("/disable")
async def disable_two_factor(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for user"""
    from shared.security.auth import verify_password
    
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.backup_codes = None
    db.commit()
    
    return {"message": "2FA disabled successfully"}
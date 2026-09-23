from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


class Security:

    def verify_password(
        self,
        user_credential_password: str,
        user_saved_password: str
    ) -> bool:
        return password_hash.verify(
            user_credential_password,
            user_saved_password
        )

    def hashed_password(self, user_password: str) -> str:
        return password_hash.hash(user_password)
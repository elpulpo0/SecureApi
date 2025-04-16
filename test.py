from backend.modules.api.auth.security import verify_password, anonymize, hash_token

word_to_hash = "chris"

word_hashed = hash_token(word_to_hash)

print(word_hashed)

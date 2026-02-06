/** In-memory store for pre-auth verification codes. */

interface StoredCode {
  code: string;
  created_at: Date;
}

export class VerificationCodeStore {
  private store = new Map<string, StoredCode>();
  private expirySeconds: number;

  constructor(expirySeconds: number = 600) {
    this.expirySeconds = expirySeconds;
  }

  store_code(email: string, code: string): void {
    this.store.set(email.toLowerCase(), { code, created_at: new Date() });
  }

  lookup(email: string): StoredCode | null {
    const entry = this.store.get(email.toLowerCase());
    if (!entry) return null;
    const expiry = new Date(entry.created_at.getTime() + this.expirySeconds * 1000);
    if (new Date() > expiry) {
      this.store.delete(email.toLowerCase());
      return null;
    }
    return entry;
  }

  remove(email: string): void {
    this.store.delete(email.toLowerCase());
  }

  cleanup(): void {
    const now = new Date();
    for (const [email, entry] of this.store) {
      const expiry = new Date(entry.created_at.getTime() + this.expirySeconds * 1000);
      if (now > expiry) {
        this.store.delete(email);
      }
    }
  }
}

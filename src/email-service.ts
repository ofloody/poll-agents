/** Email verification service. */

import nodemailer from "nodemailer";
import type { SMTPSettings } from "./config/settings";

export class EmailService {
  private transporter: nodemailer.Transporter;
  private senderEmail: string;

  constructor(settings: SMTPSettings) {
    this.senderEmail = settings.sender_email;
    this.transporter = nodemailer.createTransport({
      host: settings.host,
      port: settings.port,
      secure: settings.port === 465,
      auth: {
        user: settings.username,
        pass: settings.password,
      },
      connectionTimeout: 10000,
      greetingTimeout: 10000,
      socketTimeout: 10000,
      ...(settings.use_tls && settings.port !== 465 ? { requireTLS: true } : {}),
    });
  }

  generateVerificationCode(length: number = 6): string {
    const digits = "0123456789";
    let code = "";
    for (let i = 0; i < length; i++) {
      code += digits[crypto.getRandomValues(new Uint32Array(1))[0] % 10];
    }
    return code;
  }

  async sendVerificationEmail(toEmail: string, code: string): Promise<boolean> {
    const mailOptions = {
      from: this.senderEmail,
      to: toEmail,
      subject: "Poll Agents - Verification Code",
      text: `Welcome to Poll Agents!\n\nYour verification code is: ${code}\n\nThis code will expire in 5 minutes.\n\nThank you for participating.\n`,
    };

    try {
      await this.transporter.sendMail(mailOptions);
      console.log(`[EMAIL] Verification code sent to ${toEmail}`);
      return true;
    } catch (e) {
      console.log(`[EMAIL ERROR] Failed to send to ${toEmail}: ${e}`);
      return false;
    }
  }
}

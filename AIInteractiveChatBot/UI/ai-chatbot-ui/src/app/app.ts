import { ChangeDetectorRef, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ChatService,
  ChatResponse,
  UploadResponse,
  SubmitResponse,
  UserJson
} from './services/chat';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  question = '';
  loading = false;
  uploadStatus = '';
  submitStatus = '';
  generatedUser: UserJson | null = null;

  messages: ChatMessage[] = [
    {
      sender: 'bot',
      text: "Hello. Ask me anything, upload a document, or type 'create user' to begin."
    }
  ];

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) {}

  sendMessage(): void {
    const trimmedQuestion = this.question.trim();

    if (!trimmedQuestion || this.loading) {
      return;
    }

    this.messages.push({ sender: 'user', text: trimmedQuestion });
    this.loading = true;

    this.chatService.sendMessage(trimmedQuestion).subscribe({
      next: (response: ChatResponse) => {
        this.messages.push({
          sender: 'bot',
          text: response.answer || 'No response received.'
        });

        // If backend returns user JSON, validate and fake-submit
        if (response.user) {
          this.generatedUser = response.user;

          if (this.isValidUser(response.user)) {
            this.submitStatus = 'User JSON valid. Submitting...';

            this.chatService.submitUser(response.user).subscribe({
              next: (submitResponse: SubmitResponse) => {
                this.submitStatus = submitResponse.message;
                this.messages.push({
                  sender: 'bot',
                  text: submitResponse.message
                });
                this.cdr.detectChanges();
              },
              error: () => {
                this.submitStatus = 'Fake submit failed.';
                this.messages.push({
                  sender: 'bot',
                  text: 'Fake submit failed.'
                });
                this.cdr.detectChanges();
              }
            });
          } else {
            this.submitStatus = 'Generated user JSON failed validation.';
            this.messages.push({
              sender: 'bot',
              text: 'Generated user JSON failed validation.'
            });
          }
        }

        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.messages.push({
          sender: 'bot',
          text: 'Error connecting to backend.'
        });
        this.loading = false;
        this.cdr.detectChanges();
      }
    });

    this.question = '';
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      return;
    }

    const file = input.files[0];
    this.uploadStatus = `Uploading ${file.name}...`;

    this.chatService.uploadFile(file).subscribe({
      next: (response: UploadResponse) => {
        this.uploadStatus = `${response?.source || file.name} uploaded successfully. Indexed ${response?.count ?? 0} chunks.`;

        this.messages.push({
          sender: 'bot',
          text: `${response?.source || file.name} uploaded successfully. You can now ask questions about it.`
        });

        this.cdr.detectChanges();
      },
      error: () => {
        this.uploadStatus = 'File upload failed.';
        this.messages.push({
          sender: 'bot',
          text: 'Sorry, file upload failed.'
        });
        this.cdr.detectChanges();
      }
    });

    input.value = '';
  }

  isValidUser(user: UserJson): boolean {
    if (!user.firstName?.trim()) {
      return false;
    }

    if (!user.lastName?.trim()) {
      return false;
    }

    if (!user.email?.trim()) {
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(user.email);
  }
}
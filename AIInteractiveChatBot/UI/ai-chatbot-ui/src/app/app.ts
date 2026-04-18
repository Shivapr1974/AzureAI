import { ChangeDetectorRef, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, UploadResponse } from './services/chat';


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

  messages: ChatMessage[] = [
    { sender: 'bot', text: 'Hello. Ask me anything, or upload a document first.' }
  ];

  constructor(private chatService: ChatService,
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
      next: (response: any) => {
        this.messages.push({
          sender: 'bot',
          text: response.answer || 'No response received.'
        });
        this.loading = false;
      },
      error: () => {
        this.messages.push({
          sender: 'bot',
          text: 'Error connecting to backend.'
        });
        this.loading = false;
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
        this.uploadStatus =
        `${response?.source || file.name} uploaded successfully.`;

        this.messages.push({
          sender: 'bot',
          text: `${response?.source || file.name} uploaded successfully. You can now ask questions about it.`
        });
        this.cdr.detectChanges()
      },
      error: () => {
        this.uploadStatus = 'File upload failed.';
        this.messages.push({
          sender: 'bot',
          text: 'Sorry, file upload failed.'
        });
        this.cdr.detectChanges()
      }
    });

    input.value = '';
  }
}
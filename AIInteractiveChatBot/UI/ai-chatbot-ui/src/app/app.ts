import { ChangeDetectorRef, Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ChatService,
  ChatResponse,
  UploadResponse,
  UserJson,
  StudentJson,
  BcFormJson
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
  @ViewChild('chatWindow') chatWindow!: ElementRef;
  question = '';
  loading = false;
  uploadStatus = '';
  agentStatus = '';
  generatedUser: UserJson | null = null;
  generatedStudent: StudentJson | null = null;
  generatedBcForm: BcFormJson | null = null;

  messages: ChatMessage[] = [
    {
      sender: 'bot',
      text: "Hello. Ask me anything, upload a document, or type 'create user' or 'create student' to begin."
    }
  ];

  constructor(
    private chatService: ChatService,
    private cdr: ChangeDetectorRef
  ) {}

  scrollToBottom() {
    try {
      this.chatWindow.nativeElement.scrollTop =
        this.chatWindow.nativeElement.scrollHeight;
    } catch (err) {}
  }
  startWorkflow(command: string): void {
    if (this.loading) {
      return;
    }

    this.question = command;
    this.sendMessage();
  }
  sendMessage(): void {
    const trimmedQuestion = this.question.trim();

    if (!trimmedQuestion || this.loading) {
      return;
    }

    this.messages.push({ sender: 'user', text: trimmedQuestion });
    this.loading = true;
    this.question = '';
    this.scrollToBottom()
    this.chatService.sendMessage(trimmedQuestion).subscribe({
      next: (response: ChatResponse) => {
        this.messages.push({
          sender: 'bot',
          text: response.answer || 'No response received.'
        });
        setTimeout(() => this.scrollToBottom(), 0);
        this.generatedUser = response.user ?? null;
        this.generatedStudent = response.student ?? null;
        this.generatedBcForm = response.bcForm?? null;

        if (response.user) {
          this.agentStatus = 'User flow completed.';
        } else if (response.student) {
          this.agentStatus = 'Student flow completed.';
        } else {
          this.agentStatus = response.mode ? `Mode: ${response.mode}` : '';
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
}
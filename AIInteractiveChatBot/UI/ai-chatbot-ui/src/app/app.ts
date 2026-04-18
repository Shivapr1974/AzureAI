import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from './services/chat';

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

  messages: ChatMessage[] = [
    { sender: 'bot', text: 'Hello. Ask me anything.' }
  ];

  constructor(private chatService: ChatService) {}

  sendMessage(): void {
    const trimmedQuestion = this.question.trim();

    if (!trimmedQuestion || this.loading) {
      return;
    }

    this.messages.push({ sender: 'user', text: trimmedQuestion });
    this.loading = true;

    this.chatService.sendMessage(trimmedQuestion).subscribe({
      next: (response) => {
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
}
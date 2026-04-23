import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  AgentReviewResult,
  AppState,
  ChatService,
  FormState,
  SuggestedChip
} from '../services/chat';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-page.html',
  styleUrl: './chat-page.css'
})
export class ChatPageComponent implements OnInit {
  state: AppState | null = null;
  draftForm: FormState = this.emptyForm();
  suggestedChips: SuggestedChip[] = [];
  message = '';
  lastStatus = 'Chat with Cora to start filling the form or upload docs first.';
  busy = false;

  readonly state$;
  readonly chips$;

  constructor(private readonly chatService: ChatService) {
    this.state$ = this.chatService.state$;
    this.chips$ = this.chatService.chips$;
  }

  ngOnInit(): void {
    this.chatService.state$.subscribe((state) => {
      this.state = state;
      if (state) {
        this.draftForm = { ...state.form };
      }
    });

    this.chatService.chips$.subscribe((chips) => {
      this.suggestedChips = chips;
    });
  }

  sendMessage(): void {
    const trimmed = this.message.trim();
    if (!trimmed || this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.sendMessage(trimmed).subscribe({
      next: (response) => {
        this.lastStatus = response.answer ?? 'Message sent.';
        this.message = '';
        this.busy = false;
      },
      error: () => {
        this.lastStatus = 'Unable to reach the backend.';
        this.busy = false;
      }
    });
  }

  applyChip(chip: SuggestedChip): void {
    if (this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.sendMessage('', chip).subscribe({
      next: (response) => {
        this.lastStatus = response.answer ?? `Applied ${chip.label}.`;
        this.busy = false;
      },
      error: () => {
        this.lastStatus = `Unable to apply ${chip.label}.`;
        this.busy = false;
      }
    });
  }

  saveForm(): void {
    if (this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.saveForm(this.draftForm).subscribe({
      next: (response) => {
        this.lastStatus = response.answer ?? 'Form saved.';
        this.busy = false;
      },
      error: () => {
        this.lastStatus = 'Form save failed.';
        this.busy = false;
      }
    });
  }

  submitForReview(): void {
    if (this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.submit(this.draftForm).subscribe({
      next: (response) => {
        this.lastStatus = response.answer ?? 'Submitted for review.';
        this.busy = false;
      },
      error: () => {
        this.lastStatus = 'Submit failed.';
        this.busy = false;
      }
    });
  }

  rerunReview(): void {
    if (this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.review(this.draftForm).subscribe({
      next: (response) => {
        this.lastStatus = response.answer ?? 'Review refreshed.';
        this.busy = false;
      },
      error: () => {
        this.lastStatus = 'Review failed.';
        this.busy = false;
      }
    });
  }

  agentEntries(): Array<[string, AgentReviewResult]> {
    return Object.entries(this.state?.review.agentResults ?? {});
  }

  trackByAgent(index: number, entry: [string, AgentReviewResult]): string {
    return `${index}-${entry[0]}`;
  }

  private emptyForm(): FormState {
    return {
      intType: '',
      reqType: '',
      intName: '',
      inOverview: '',
      inHighlights: ''
    };
  }
}

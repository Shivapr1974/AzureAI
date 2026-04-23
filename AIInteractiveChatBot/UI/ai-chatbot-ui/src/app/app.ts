import { AsyncPipe, CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ChatService } from './services/chat';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    AsyncPipe,
    CommonModule,
    RouterLink,
    RouterLinkActive,
    RouterOutlet
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  readonly state$;
  resetting = false;

  constructor(private readonly chatService: ChatService) {
    this.state$ = this.chatService.state$;
  }

  ngOnInit(): void {
    this.chatService.loadState().subscribe();
  }

  startFresh(): void {
    if (this.resetting) {
      return;
    }

    this.resetting = true;
    this.chatService.resetSession().subscribe({
      next: () => {
        this.resetting = false;
      },
      error: () => {
        this.resetting = false;
      }
    });
  }
}

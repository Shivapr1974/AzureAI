import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AppState, ChatService, EvidenceItem } from '../services/chat';

@Component({
  selector: 'app-documents-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './documents-page.html',
  styleUrl: './documents-page.css'
})
export class DocumentsPageComponent implements OnInit {
  state: AppState | null = null;
  uploadStatus = 'Upload TXT or PDF files to index them into ChromaDB.';
  searchQuery = '';
  searchResults: EvidenceItem[] = [];
  busy = false;
  deletingSource = '';

  constructor(private readonly chatService: ChatService) {}

  ngOnInit(): void {
    this.chatService.state$.subscribe((state) => {
      this.state = state;
    });

    this.chatService.listDocuments().subscribe();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || this.busy) {
      return;
    }

    this.busy = true;
    this.uploadStatus = `Uploading ${file.name}...`;

    this.chatService.uploadFile(file).subscribe({
      next: (response) => {
        this.uploadStatus = response.message;
        this.busy = false;
      },
      error: () => {
        this.uploadStatus = 'Upload failed.';
        this.busy = false;
      }
    });

    input.value = '';
  }

  searchDocs(): void {
    const query = this.searchQuery.trim();
    if (!query || this.busy) {
      return;
    }

    this.busy = true;
    this.chatService.searchDocuments(query).subscribe({
      next: (response) => {
        this.searchResults = response.results;
        this.busy = false;
      },
      error: () => {
        this.searchResults = [];
        this.busy = false;
      }
    });
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.searchResults = [];
  }

  removeDocument(source: string): void {
    if (!source || this.busy) {
      return;
    }

    this.busy = true;
    this.deletingSource = source;
    this.uploadStatus = `Removing ${source}...`;

    this.chatService.deleteDocument(source).subscribe({
      next: (response) => {
        this.uploadStatus = response.message;
        this.searchResults = this.searchResults.filter((item) => item.source !== source);
        this.busy = false;
        this.deletingSource = '';
      },
      error: () => {
        this.uploadStatus = `Unable to remove ${source}.`;
        this.busy = false;
        this.deletingSource = '';
      }
    });
  }
}

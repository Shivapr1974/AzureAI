import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  text: string;
  intent: string;
}

export interface ReviewFinding {
  id: string;
  priority: number;
  message: string;
  recommendation: string;
  scoreImpact: number;
}

export interface EvidenceItem {
  source: string;
  chunk: number | string;
  text: string;
  distance?: number | null;
}

export interface AgentReviewResult {
  status: string;
  findings: ReviewFinding[];
  score: number;
  summary: string;
  evidence: EvidenceItem[];
  isMock: boolean;
}

export interface ReviewState {
  status: string;
  agentResults: Record<string, AgentReviewResult>;
  scores: Record<string, number | string>;
  summary: string;
  isMock: boolean;
}

export interface FormState {
  intType: string;
  reqType: string;
  intName: string;
  inOverview: string;
  inHighlights: string;
}

export interface DocumentRecord {
  source: string;
  chunkCount: number;
}

export interface RetrievalState {
  query: string;
  context: EvidenceItem[];
  documents: DocumentRecord[];
}

export interface AppState {
  sessionId: string;
  mode: string;
  form: FormState;
  chat: {
    history: ChatHistoryItem[];
  };
  retrieval: RetrievalState;
  review: ReviewState;
}

export interface SuggestedChip {
  label: string;
  value: string;
  field: string | null;
  multiSelect: boolean;
}

export interface ApiResponse {
  sessionId: string;
  answer?: string;
  intent?: string;
  suggestedChips?: SuggestedChip[];
  appState?: AppState;
}

export interface UploadResponse {
  message: string;
  count: number;
  source: string;
  appState?: AppState;
  sessionId?: string;
}

export interface SearchDocsResponse {
  sessionId: string;
  results: EvidenceItem[];
  appState?: AppState;
}

export interface DocumentsResponse {
  sessionId: string;
  documents: DocumentRecord[];
  appState?: AppState;
}

export interface DeleteDocumentResponse {
  message: string;
  deleted: number;
  source: string;
  sessionId: string;
  documents: DocumentRecord[];
  appState?: AppState;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiBase = 'http://127.0.0.1:8000';
  private readonly storageKey = 'formiq-session-id';
  private sessionId = this.readSessionId();

  private readonly stateSubject = new BehaviorSubject<AppState | null>(null);
  private readonly chipsSubject = new BehaviorSubject<SuggestedChip[]>([]);

  readonly state$ = this.stateSubject.asObservable();
  readonly chips$ = this.chipsSubject.asObservable();

  constructor(private readonly http: HttpClient) {}

  loadState(): Observable<ApiResponse> {
    const params = this.sessionId ? new HttpParams().set('sessionId', this.sessionId) : undefined;
    return this.http
      .get<ApiResponse>(`${this.apiBase}/state`, { params })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  sendMessage(message: string, chip?: SuggestedChip): Observable<ApiResponse> {
    return this.http
      .post<ApiResponse>(`${this.apiBase}/chat`, {
        sessionId: this.sessionId,
        message,
        chip: chip ?? null
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  saveForm(form: FormState): Observable<ApiResponse> {
    return this.http
      .post<ApiResponse>(`${this.apiBase}/form`, {
        sessionId: this.sessionId,
        form
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  submit(form: FormState): Observable<ApiResponse> {
    return this.http
      .post<ApiResponse>(`${this.apiBase}/submit`, {
        sessionId: this.sessionId,
        form
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  resetSession(): Observable<ApiResponse> {
    return this.http
      .post<ApiResponse>(`${this.apiBase}/reset`, {
        sessionId: this.sessionId
      })
      .pipe(
        tap((response) => {
          this.updateClientState(response);
          this.chipsSubject.next(response.suggestedChips ?? []);
        })
      );
  }

  review(form: FormState): Observable<ApiResponse> {
    return this.http
      .post<ApiResponse>(`${this.apiBase}/review`, {
        sessionId: this.sessionId,
        form
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  uploadFile(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (this.sessionId) {
      formData.append('sessionId', this.sessionId);
    }

    return this.http
      .post<UploadResponse>(`${this.apiBase}/upload`, formData)
      .pipe(tap((response) => this.updateClientState(response)));
  }

  listDocuments(): Observable<DocumentsResponse> {
    const params = this.sessionId ? new HttpParams().set('sessionId', this.sessionId) : undefined;
    return this.http
      .get<DocumentsResponse>(`${this.apiBase}/documents`, { params })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  deleteDocument(source: string): Observable<DeleteDocumentResponse> {
    return this.http
      .post<DeleteDocumentResponse>(`${this.apiBase}/documents/delete`, {
        sessionId: this.sessionId,
        source
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  searchDocuments(query: string): Observable<SearchDocsResponse> {
    return this.http
      .post<SearchDocsResponse>(`${this.apiBase}/search-docs`, {
        sessionId: this.sessionId,
        query
      })
      .pipe(tap((response) => this.updateClientState(response)));
  }

  private updateClientState(response: {
    sessionId?: string;
    appState?: AppState;
    suggestedChips?: SuggestedChip[];
  }): void {
    if (response.sessionId) {
      this.sessionId = response.sessionId;
      this.writeSessionId(response.sessionId);
    }

    if (response.appState) {
      this.stateSubject.next(response.appState);
    }

    if (response.suggestedChips) {
      this.chipsSubject.next(response.suggestedChips);
    }
  }

  private readSessionId(): string {
    try {
      return localStorage.getItem(this.storageKey) ?? '';
    } catch {
      return '';
    }
  }

  private writeSessionId(sessionId: string): void {
    try {
      localStorage.setItem(this.storageKey, sessionId);
    } catch {
      // Ignore environments without storage.
    }
  }
}

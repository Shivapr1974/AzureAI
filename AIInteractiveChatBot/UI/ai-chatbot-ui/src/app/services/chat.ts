import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserJson {
  firstName: string;
  lastName: string;
  email: string;
}

export interface StudentJson {
  studentId: string;
  firstName: string;
  lastName: string;
  email: string;
  grade: string;
}

export interface ChatResponse {
  answer: string;
  user?: UserJson;
  student?: StudentJson;
  mode?: string;
}

export interface UploadResponse {
  message: string;
  count: number;
  source: string;
  path?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private chatUrl = 'http://127.0.0.1:8000/chat';
  private uploadUrl = 'http://127.0.0.1:8000/upload';

  constructor(private http: HttpClient) {}

  sendMessage(question: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(this.chatUrl, { question });
  }

  uploadFile(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(this.uploadUrl, formData);
  }
}
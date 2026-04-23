import { Routes } from '@angular/router';

import { ChatPageComponent } from './pages/chat-page';
import { DocumentsPageComponent } from './pages/documents-page';
import { HomePageComponent } from './pages/home-page';

export const routes: Routes = [
  { path: '', component: HomePageComponent, pathMatch: 'full' },
  { path: 'chat', component: ChatPageComponent },
  { path: 'documents', component: DocumentsPageComponent },
  { path: '**', redirectTo: '' }
];

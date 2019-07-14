import { Observable } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Settings } from './settings';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {

  constructor(private http: HttpClient) { }

  generateNewCerts(): Observable<Settings> {
    return this.http.post<Settings>(`/api/cacert/generate`, {});
  }

  setSettings(settings: Settings): Observable<Settings> {
    return this.http.post<Settings>(`/api/settings`, settings);
  }

  getSettings(): Observable<Settings> {
    return this.http.get<Settings>(`/api/settings`);
  }
}

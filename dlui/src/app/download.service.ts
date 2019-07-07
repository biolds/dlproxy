import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Download } from './download';

@Injectable({
  providedIn: 'root'
})
export class DownloadService {

  constructor(private http: HttpClient) { }

  getDownload(id: number): Observable<Download> {
    return this.http.get<Download>(`/api/download/get/${id}`);
  }

  saveDownload(id: number): Observable<any> {
    return this.http.post(`/api/download/save/${id}`, {});
  }
}

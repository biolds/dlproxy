import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Download } from './download';
import { ObjList } from './objlist';

@Injectable({
  providedIn: 'root'
})
export class DownloadService {

  constructor(private http: HttpClient) { }

  private handleError<T> (operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {

      // TODO: send the error to remote logging infrastructure
      console.error(error); // log to console instead

      // TODO: better job of transforming error for user consumption
      console.log(`${operation} failed: ${error.message}`);

      // Let the app keep running by returning an empty result.
      return of(result as T);
    };
  }

  getDownload(id: number): Observable<Download> {
    return this.http.get<Download>(`/api/download/get/${id}`)
      .pipe(
        catchError(this.handleError<Download>('getDownload', {
          id: 0,
          url: {id: 0, url: ''},
          date: 0,
          filesize: 0,
          filename: '',
          mimetype: '',
          current_size: 0,
          to_keep: false,
          downloaded: false,
          bandwidth: null,
          stats_date: 0,
          error: null
        }))
      );
  }

  downloadList(): Observable<ObjList<Download>> {
    return this.http.get<ObjList<Download>>(`/api/downloads`);
  }

  saveDownload(id: number): Observable<any> {
    return this.http.post(`/api/download/save/${id}`, {});
  }

  deleteDownload(id: number): Observable<any> {
    return this.http.post(`/api/download/delete/${id}`, {});
  }
}

import { Observable } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { ObjList, ObjListWithDates } from './objlist';
import { UrlAccess } from './url-access';

@Injectable({
  providedIn: 'root'
})
export class UrlService {

  constructor(private http: HttpClient) { }

  getUrlAccessesWithDates(offset: number, limit: number, filter: string): Observable<ObjListWithDates<UrlAccess>> {
    let url = `/api/urls?offset=${offset}&limit=${limit}&with_dates=1`;
    if (filter) {
      url += `&${filter}`;
    }
    return this.http.get<ObjListWithDates<UrlAccess>>(url);
  }

  getUrlAccesses(offset: number, limit: number, filter: string): Observable<ObjList<UrlAccess>> {
    let url = `/api/urls?offset=${offset}&limit=${limit}`;
    if (filter) {
      url += `&${filter}`;
    }
    return this.http.get<ObjList<UrlAccess>>(url);
  }
}

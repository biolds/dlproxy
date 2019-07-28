import { Observable } from 'rxjs';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { ObjList } from './objlist';
import { UrlAccess } from './url-access';

@Injectable({
  providedIn: 'root'
})
export class UrlService {

  constructor(private http: HttpClient) { }

  getUrlAccesses(offset: number, limit: number, filter: string): Observable<ObjList<UrlAccess>> {
    let url = `/api/urls?offset=${offset}&limit=${limit}`;
    if (filter) {
      url += `&${filter}`;
    }
    return this.http.get<ObjList<UrlAccess>>(url);
  }
}

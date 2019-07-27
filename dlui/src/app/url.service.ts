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

  getUrlAccesses(): Observable<ObjList<UrlAccess>> {
    return this.http.get<ObjList<UrlAccess>>('/api/urls');
  }
}

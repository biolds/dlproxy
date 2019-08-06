import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';

import { ObjList } from './objlist';
import { SearchEngine } from './search-engine';

@Injectable({
  providedIn: 'root'
})
export class SearchEngineService {

  constructor(private http: HttpClient) { }

  searchEngineList(): Observable<ObjList<SearchEngine>> {
    return this.http.get<ObjList<SearchEngine>>('/api/search_engines');
  }
}

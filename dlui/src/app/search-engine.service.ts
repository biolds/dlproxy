import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';

import { ObjList } from './objlist';
import { SearchEngine } from './search-engine';
import { Search } from './search';

@Injectable({
  providedIn: 'root'
})
export class SearchEngineService {

  constructor(private http: HttpClient) { }

  lastSearches(): Observable<ObjList<Search>> {
    return this.http.get<ObjList<Search>>('/api/last_searches');
  }

  searchEngineList(): Observable<ObjList<SearchEngine>> {
    return this.http.get<ObjList<SearchEngine>>('/api/search_engines');
  }
}

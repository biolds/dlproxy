import { Component, Input, OnInit } from '@angular/core';

import { ObjList } from '../objlist';
import { Search } from '../search';

@Component({
  selector: 'app-search-log',
  templateUrl: './search-log.component.html',
  styleUrls: ['./search-log.component.css']
})
export class SearchLogComponent implements OnInit {
  @Input() lastSearches: ObjList<Search>;

  constructor() { }

  searchURL(s: Search, terms: string) {
    return '/search/' + s.search_engine.id + '?q=' + encodeURIComponent(s.query);
  }

  ngOnInit() {
  }
}

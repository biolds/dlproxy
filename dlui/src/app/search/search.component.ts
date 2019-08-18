import { Component, OnInit, isDevMode } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { DomSanitizer } from '@angular/platform-browser';
import { ActivatedRoute } from '@angular/router';

import { ObjList } from '../objlist';
import { Search } from '../search';
import { SearchEngineService } from '../search-engine.service';
import { SearchEngine } from '../search-engine';


// Copy / paste from https://github.com/angular/angular/blob/b667bd2224064f4d53518fec96f9cc3b6ac49817/packages/core/src/sanitization/url_sanitizer.ts#L42
// With DATA_URL_PATTERN regexp updated

const SAFE_URL_PATTERN = /^(?:(?:https?|mailto|ftp|tel|file):|[^&:/?#]*(?:[/?#]|$))/gi;

/** A pattern that matches safe data URLs. Only matches image, video and audio types. */
const DATA_URL_PATTERN =
    /^data:(?:image\/(?:[a-z-_+]+)|video\/(?:mpeg|mp4|ogg|webm)|audio\/(?:mp3|oga|ogg|opus));base64,[a-z0-9+\/]+=*$/i;

export function _sanitizeUrl(url: string): string {
  url = String(url);
  if (url.match(SAFE_URL_PATTERN) || url.match(DATA_URL_PATTERN)) return url;

  if (isDevMode()) {
    console.warn(`WARNING: sanitizing unsafe URL value ${url} (see http://g.co/ng/security#xss)`);
  }

  return 'unsafe:' + url;
}


@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent implements OnInit {
  searchForm = this.fb.group({
    search: '',
    searchEngine: 0,
  });
  searchEngines: SearchEngine[];
  selectedSE: SearchEngine;
  searchUrl: string;
  lastSearches: ObjList<Search>;

  constructor(
    private fb: FormBuilder,
    private searchEngineService: SearchEngineService,
    private sanitizer: DomSanitizer,
    private route: ActivatedRoute
  ) {
  }

  updateSelectedSE() {
    this.selectedSE = this.searchEngines.filter(se => se.id === this.searchForm.value.searchEngine)[0];
  }

  runSearch() {
    let path = '/search/' + this.selectedSE.id;
    window.location.href = path + '?q=' + this.searchForm.value.search;
  }

  openSearch(search: Search) {
    let path = '/search/' + search.search_engine.id;
    window.location.href = path + '?q=' + search.query;
  }

  ngOnInit() {
    this.searchEngineService.searchEngineList().subscribe((searchEngines) => {
      this.searchEngines = searchEngines.objs.map(se => {
        let icon = this.sanitizer.bypassSecurityTrustUrl(_sanitizeUrl(se.icon));
        return {
          ...se,
          icon: icon
        } as SearchEngine;
      });
      
      this.selectedSE = this.searchEngines[0];
      let seId = searchEngines.objs[0].id;

      this.searchForm.patchValue({ searchEngine: seId });
    });
    this.searchEngineService.lastSearches().subscribe((lastSearches) => {
      this.lastSearches = lastSearches;
      this.lastSearches.objs = lastSearches.objs.map(search => {
        let d = new Date(0);
        d.setUTCSeconds(search.date);
        const s = {
            ...search,
            date_str: d.toLocaleString()
        } as Search;
        return s;
      });
    });
  }
}

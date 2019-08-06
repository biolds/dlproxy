import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { Observable, Subject, of } from 'rxjs';
import { FormBuilder } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MAT_MOMENT_DATE_FORMATS, MomentDateAdapter } from '@angular/material-moment-adapter';
import { DateAdapter, MAT_DATE_FORMATS, MAT_DATE_LOCALE } from '@angular/material/core';
import * as moment from 'moment';


import { ObjList } from '../objlist';
import { UrlAccess, URL_HEIGHT, FilteredPath } from '../url-access';
import { UrlService } from '../url.service';

// https://stackoverflow.com/questions/3561493/is-there-a-regexp-escape-function-in-javascript/3561711
function reEscape (s: string): string {
    return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
};

@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css'],
  providers: [
    {provide: DateAdapter, useClass: MomentDateAdapter, deps: [MAT_DATE_LOCALE]},
    {provide: MAT_DATE_FORMATS, useValue: MAT_MOMENT_DATE_FORMATS},
  ]
})
export class HistoryComponent implements OnInit {
  @ViewChild('historyList', {static: false}) historyList;
  viewForm = this.fb.group({
    search: '',
    startDate: 0,
    endDate: 0,
    mimeFilter: ['webpages'],
    httpStatus: ['2'],
  });
  interval: number;
  yPos: number;
  urlsHeight: number;
  urlsTop: number;
  urls: ObjList<UrlAccess>;
  positions$: Observable<number>;
  loading = false;
  private scrollPosition = new Subject<number>();

  constructor(
    private urlService: UrlService,
    private fb: FormBuilder) {
  }

  trackByUrls(index: number, url: UrlAccess): number {
    return url.id;
  }

  getUrls(position: number) {
    const urlMax = position + (Math.round(window.innerHeight * 2 / URL_HEIGHT));
    let urlMin = position - (Math.round(window.innerHeight / URL_HEIGHT));
    urlMin = urlMin < 0 ? 0 : urlMin;

    let startDate = this.viewForm.value.startDate.hours(0).minutes(0).seconds(0).unix();
    let endDate = this.viewForm.value.endDate.hours(0).minutes(0).seconds(0).unix();
    endDate += 60 * 60 * 24;

    let filter = `f_date__gte=${startDate}&f_date__lt=${endDate}`;

    if (this.viewForm.value.mimeFilter === 'webpages') {
      filter += '&f_url__mimetype=text/html';
    }

    const searchTerms = this.viewForm.value.search.split(' ').filter(s => s !== '').map(s => s.toLowerCase());
    if (searchTerms.length !== '') {
      const urls = searchTerms.map(u => `&f_url__url__ilike=${u}`);
      filter += urls.join('');
    }

    if (this.viewForm.value.httpStatus !== 'all') {
      let s = this.viewForm.value.httpStatus;
      s = parseInt(s, 10);
      console.log('status:', s);
      filter += `&f_status__gte=${s}00&f_status__lt=${s + 1}00`;
    }

    this.urlService.getUrlAccesses(urlMin, urlMax - urlMin, filter).subscribe((urls) => {
      this.urls = urls;
      this.urlsHeight = this.urls.count * URL_HEIGHT;
      this.urlsTop = urlMin * URL_HEIGHT;
      this.updateLoading();

      if (searchTerms.length !== 0) {
        const regexpTerms = '(' + searchTerms.map(s => reEscape(s)).join('|') + ')';
        console.log('regexp terms', regexpTerms);
        const regexp = new RegExp(regexpTerms, 'i');

        this.urls.objs = this.urls.objs.map(u => {
          let paths = u.url.url.split(regexp);
          return {
            ...u,
            paths: paths.map(p => {
              return {
                path: p,
                matching: searchTerms.indexOf(p.toLowerCase()) !== -1
              } as FilteredPath;
            })
          };
        });
        console.log('filteredUrls', this.urls.objs);
      } else {
        this.urls.objs = this.urls.objs.map(u => {
          let filteredPath = {
            path: u.url.url,
            matching: false
          } as FilteredPath;
          return {
            ...u,
            paths: [filteredPath]
          };
        });
      }
    });
  }

  updateLoading() {
    const windowBottom = this.scrollVal() + window.innerHeight - URL_HEIGHT;
    const displayedHeight = this.urls.objs.length * URL_HEIGHT;
    const availableHeight = this.urls.count * URL_HEIGHT;

    this.loading = this.scrollVal() < this.urlsTop;
    this.loading = this.loading || (windowBottom > this.urlsTop + displayedHeight) && (windowBottom < availableHeight);
  }

  scrollVal(): number {
    let scrollY = window.scrollY - this.yPos;
    scrollY = scrollY < 0 ? 0 : scrollY;
    return scrollY;
  }

  @HostListener('window:scroll', ['$event'])
  scrollHandler(event) {
    this.scrollPosition.next(Math.round(this.scrollVal() / URL_HEIGHT));
    this.updateLoading();
  }

  refreshUrls() {
    this.getUrls(Math.round(this.scrollVal() / URL_HEIGHT));
  }

  ngOnDestroy() {
    clearInterval(this.interval);
  }

  ngAfterViewInit() {
    this.yPos = this.historyList.nativeElement.offsetTop;
  }

  ngOnInit() {
    this.viewForm.patchValue({startDate: moment(), endDate: moment()});

    this.positions$ = this.scrollPosition.pipe(
      // wait 100ms after each keystroke before considering the term
      debounceTime(100),

      // ignore new term if same as previous term
      distinctUntilChanged(),

      // switch to new search observable each time the term changes
      switchMap((position: number) => of(position))
    )
    this.positions$.subscribe(position => {
      this.getUrls(position);
    });

    this.scrollPosition.next(0);
    this.interval = setInterval(() => {
      this.refreshUrls();
    }, 5000);
  }
}

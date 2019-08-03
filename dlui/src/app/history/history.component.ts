import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { Observable, Subject, of } from 'rxjs';
import { FormBuilder } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MAT_MOMENT_DATE_FORMATS, MomentDateAdapter } from '@angular/material-moment-adapter';
import { DateAdapter, MAT_DATE_FORMATS, MAT_DATE_LOCALE } from '@angular/material/core';
import * as moment from 'moment';


import { ObjList } from '../objlist';
import { UrlAccess, URL_HEIGHT } from '../url-access';
import { UrlService } from '../url.service';

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
    startDate: 0,
    endDate: 0,
    mimeFilter: ['webpages'],
  })
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

    if (this.viewForm.value.mimeFilter == 'webpages') {
      filter += '&f_url__mimetype=text/html';
    }

    this.urlService.getUrlAccesses(urlMin, urlMax - urlMin, filter).subscribe((urls) => {
      this.urls = urls;
      this.urlsHeight = this.urls.count * URL_HEIGHT;
      this.urlsTop = urlMin * URL_HEIGHT;
      this.updateLoading();
    });
  }

  updateLoading() {
    const windowBottom = this.scrollVal() + window.innerHeight - URL_HEIGHT;
    const displayedHeight = this.urls.objs.length * URL_HEIGHT;
    if (this.scrollVal() < this.urlsTop || windowBottom > (this.urlsTop + displayedHeight)) {
      this.loading = true;
    } else {
      this.loading = false;
    }
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

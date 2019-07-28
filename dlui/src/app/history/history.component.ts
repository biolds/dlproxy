import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { Observable, Subject, of } from 'rxjs';
import { FormBuilder } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { ObjList } from '../objlist';
import { UrlAccess, URL_HEIGHT } from '../url-access';
import { UrlService } from '../url.service';

@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {
  @ViewChild('historyList', {static: false}) historyList;
  viewForm = this.fb.group({
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

    let filter = '';
    console.log('mime', this.viewForm.value.mimeFilter);
    if (this.viewForm.value.mimeFilter == 'webpages') {
      filter = 'f_url__mimetype=text/html';
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

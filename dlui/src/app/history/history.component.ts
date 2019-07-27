import { Component, OnInit } from '@angular/core';
import { ObjList } from '../objlist';
import { UrlAccess } from '../url-access';
import { UrlService } from '../url.service';

@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {
  interval: number;
  urls: ObjList<UrlAccess>;

  constructor(private urlService: UrlService) { }

  getUrls() {
    this.urlService.getUrlAccesses().subscribe((urls) => {
      this.urls = urls;
    });
  }

  ngOnDestroy() {
    clearInterval(this.interval);
  }

  ngOnInit() {
    this.getUrls();
    this.interval = setInterval(() => {
      this.getUrls();
    }, 5000);
  }
}

import { Component, OnInit } from '@angular/core';
import { DownloadService } from '../download.service';
import { Download } from '../download';
import { ObjList } from '../objlist';

@Component({
  selector: 'app-downloads',
  templateUrl: './downloads.component.html',
  styleUrls: ['./downloads.component.css']
})
export class DownloadsComponent implements OnInit {
  downloads: ObjList<Download>;

  constructor(
    private downloadService: DownloadService,
  ) { }

  getDownloads(): void {
    this.downloadService.downloadList().subscribe((downloads) => {
      this.downloads = downloads;
      console.log('got downloads:', downloads);
    })
  }

  ngOnInit() {
    this.getDownloads();
  }
}

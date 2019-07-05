import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { Download } from '../download';
import { DownloadService } from '../download.service'

@Component({
  selector: 'app-download',
  templateUrl: './download.component.html',
  styleUrls: ['./download.component.css']
})
export class DownloadComponent implements OnInit {
  download: Download;

  constructor(
    private downloadService: DownloadService,
    private route: ActivatedRoute
  ) { }

  getDownload(): void {
    this.download = this.downloadService.getDownload();
  }

  ngOnInit() {
    this.getDownload();
  }
}

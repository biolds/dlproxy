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
  progress: number;
  dismissed: boolean;
  size: string;

  constructor(
    private downloadService: DownloadService,
    private route: ActivatedRoute
  ) {}

  getDownload(): void {
    const id = +this.route.snapshot.paramMap.get('id');
    this.downloadService.getDownload(id)
      .subscribe(download => {
        this.download = download;
        this.progress = download.current_size / download.filesize * 100;


        const unit = ['', 'k', 'M', 'G', 'T'];
        let i = 0;
        let size = download.filesize;

        while (size > 1024) {
          size /= 1024;
          i++;
        }
        size = Math.round(size);
        this.size = `${size}${unit[i]}B`;
      });
  }

  fileDownload(): void {
    this.dismissed = true;
  }

  saveDownload(): void {
    this.downloadService.saveDownload(this.download.id).subscribe(() => {
      window.history.back();
    });
  }

  cancelDownload(): void {
    this.downloadService.deleteDownload(this.download.id).subscribe(() => {
      window.history.back();
    });
  }

  ngOnInit() {
    this.progress = 0;
    this.dismissed = false;
    this.getDownload();
  }
}
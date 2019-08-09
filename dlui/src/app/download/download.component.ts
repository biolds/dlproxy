import { Component, OnInit, Inject, Input } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Download } from '../download';
import { DownloadService } from '../download.service';

@Component({
  selector: 'app-download',
  templateUrl: './download.component.html',
  styleUrls: ['./download.component.css']
})
export class DownloadComponent implements OnInit {
  @Input() downloadData: Download;
  download: Download;
  progress: number;
  bandwidth: string;
  eta: string;
  downloadStarted: boolean;
  size: string;
  interval: number;
  canOpen: boolean;

  constructor(
    private downloadService: DownloadService,
    private route: ActivatedRoute,
    public dialog: MatDialog
  ) {}

  humanSize(size: number): string {
    const unit = ['', 'k', 'M', 'G', 'T'];
    let i = 0;

    while (size > 1024) {
      size /= 1024;
      i++;
    }
    size = Math.round(size);
    return `${size} ${unit[i]}B`;
  }

  humanETA(eta: number): string {
    if (eta < 60) {
      return Math.round(eta) + ' seconds';
    }
    eta /= 60;

    if (eta < 60) {
      return Math.round(eta) + ' minutes';
    }

    if (eta < 24 * 60) {
      return Math.trunc(eta / 60) + ':' + Math.round(eta % 60);
    }

    eta /= 24 * 60;
    eta = Math.round(eta);
    return `${eta} day` + ((eta >= 2) ? 's' : '');
  }

  loadData(download: Download): void {
    this.download = download;
    this.progress = download.current_size / download.filesize * 100;
    this.size = this.humanSize(download.current_size);

    if (download.bandwidth !== null) {
        this.bandwidth = this.humanSize(download.bandwidth) + '/s';

        let eta = (download.filesize - download.current_size);
        eta -= ((Date.now() / 1000) - download.stats_date) * download.bandwidth;
        eta /= download.bandwidth;
        this.eta =  this.humanETA(eta);
    }
  }

  getDownload(): void {
    const id = +this.route.snapshot.paramMap.get('id');
    this.downloadService.getDownload(id)
      .subscribe(download => {
        if (this.downloadStarted && download.id === 0) {
          window.history.back();
        }

        this.loadData(download);
      });
  }

  fileDownload(): void {
    this.downloadStarted = true;
    window.location.pathname = `/direct_download/${this.download.id}`;
  }

  saveDownload(): void {
    this.downloadService.saveDownload(this.download.id).subscribe(() => {
      if (!this.downloadData) {
        window.history.back();
      }
    });
  }

  cancelDownload(): void {
    this.downloadService.deleteDownload(this.download.id).subscribe(() => {
      if (!this.downloadData) {
        window.history.back();
      }
    });
  }

  dlDownload(): void {
    window.location.pathname = `/dl_download/${this.download.id}`;
  }

  onDelete(): void {
    const dialogRef = this.dialog.open(DownloadCancelDialog, {
      data: this.download
    });
    dialogRef.afterClosed().subscribe(deleteConfirmed => {
      console.log('doing deleete', deleteConfirmed);
      if (deleteConfirmed) {
        this.downloadService.deleteDownload(this.download.id).subscribe();
      }
    });
  }

  ngOnDestroy() {
    clearInterval(this.interval);
  }

  ngOnInit() {
    this.progress = 0;
    this.downloadStarted = false;
    this.canOpen = false;

    if (this.downloadData) {
      this.loadData(this.downloadData);
      let prefixType: string = this.downloadData.mimetype.split('/')[0];
      if (['text', 'image', 'video'].indexOf(prefixType) !== -1) {
        this.canOpen = true;
      }
    } else {
      this.getDownload();
      this.interval = setInterval(() => {
          this.getDownload();
      }, 5000);
    }
  }
}

@Component({
  selector: 'download-cancel-dialog',
  templateUrl: 'download-cancel.html',
})
export class DownloadCancelDialog {
  constructor(
    public dialogRef: MatDialogRef<DownloadCancelDialog>,
    @Inject(MAT_DIALOG_DATA) public data: Download) {}
}

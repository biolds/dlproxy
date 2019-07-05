import { Injectable } from '@angular/core';
import { Download } from './download';

@Injectable({
  providedIn: 'root'
})
export class DownloadService {

  constructor() { }

  getDownload(): Download {
    return {
      id: 1,
      url: 'http://pouet2/'
    };
  }
}

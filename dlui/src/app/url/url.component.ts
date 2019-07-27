import { Component, OnInit, Input } from '@angular/core';

import { UrlAccess } from '../url-access';

@Component({
  selector: 'app-url',
  templateUrl: './url.component.html',
  styleUrls: ['./url.component.css']
})
export class UrlComponent implements OnInit {
  @Input() url: UrlAccess;

  constructor() { }

  ngOnInit() {
  }
}

import { Component, OnInit } from '@angular/core';
import { Error } from '../global';

export declare var error: Error;

@Component({
  selector: 'app-error',
  templateUrl: './error.component.html',
  styleUrls: ['./error.component.css']
})
export class ErrorComponent implements OnInit {
  error: Error;

  constructor() { }

  ngOnInit() {
    this.error = error;
  }
}

import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { MAT_MOMENT_DATE_FORMATS, MomentDateAdapter } from '@angular/material-moment-adapter';
import { DateAdapter, MAT_DATE_FORMATS, MAT_DATE_LOCALE } from '@angular/material/core';
import * as moment from 'moment';

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
  viewForm = this.fb.group({
    search: '',
    startDate: 0,
    endDate: 0,
    mimeFilter: ['webpages'],
    httpStatus: ['2'],
  });
  @ViewChild('historyLog', {static: false}) historyLog;
  viewMode = 'list';

  constructor(private fb: FormBuilder) {
  }

  switchView(event) {
    this.viewMode = event.value;
  }

  refreshUrls() {
    this.historyLog.refreshUrls();
  }

  ngOnInit() {
    this.viewForm.patchValue({startDate: moment(), endDate: moment()});
  }
}

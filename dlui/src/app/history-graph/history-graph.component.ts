import { Component, Input, OnInit } from '@angular/core';
import { FormGroup } from '@angular/forms';

@Component({
  selector: 'app-history-graph',
  templateUrl: './history-graph.component.html',
  styleUrls: ['./history-graph.component.css']
})
export class HistoryGraphComponent implements OnInit {
  @Input() viewForm: FormGroup;

  constructor() { }

  ngOnInit() {
  }

}

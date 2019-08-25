import { Component, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { FormGroup } from '@angular/forms';

import * as d3 from 'd3-selection';
import * as d3Scale from 'd3-scale';
import * as d3Shape from 'd3-shape';
import * as d3Array from 'd3-array';
import * as d3Axis from 'd3-axis';

class Stock {
    date: Date;
    value: number;
}

const STOCKS: Stock[] = [
    {date: new Date('2010-01-01'), value: 210.73},
    {date: new Date('2010-01-04'), value: 214.01},
    {date: new Date('2010-01-05'), value: 214.38},
    {date: new Date('2010-01-06'), value: 210.97},
    {date: new Date('2010-01-07'), value: 210.58},
    {date: new Date('2010-01-08'), value: 211.98},
    {date: new Date('2010-01-11'), value: 210.11},
    {date: new Date('2010-01-12'), value: 207.72},
    {date: new Date('2010-01-13'), value: 210.65},
    {date: new Date('2010-01-14'), value: 209.43},
    {date: new Date('2010-01-15'), value: 205.93},
    {date: new Date('2010-01-18'), value: 205.93},
    {date: new Date('2010-01-19'), value: 215.04},
    {date: new Date('2010-01-20'), value: 211.72},
    {date: new Date('2010-01-21'), value: 208.07},
    {date: new Date('2010-01-22'), value: 197.75},
    {date: new Date('2010-01-25'), value: 203.08},
    {date: new Date('2010-01-26'), value: 205.94},
    {date: new Date('2010-01-27'), value: 207.88},
    {date: new Date('2010-01-28'), value: 199.29},
    {date: new Date('2010-01-29'), value: 192.06},
    {date: new Date('2010-02-01'), value: 194.73},
    {date: new Date('2010-02-02'), value: 195.86},
    {date: new Date('2010-02-03'), value: 199.23},
    {date: new Date('2010-02-04'), value: 192.05},
    {date: new Date('2010-02-05'), value: 195.46},
    {date: new Date('2010-02-08'), value: 194.12},
    {date: new Date('2010-02-09'), value: 196.19},
    {date: new Date('2010-02-10'), value: 195.12},
    {date: new Date('2010-02-11'), value: 198.67},
    {date: new Date('2010-02-12'), value: 200.38},
    {date: new Date('2010-02-15'), value: 200.38},
    {date: new Date('2010-02-16'), value: 203.40},
    {date: new Date('2010-02-17'), value: 202.55},
    {date: new Date('2010-02-18'), value: 202.93},
    {date: new Date('2010-02-19'), value: 201.67},
    {date: new Date('2010-02-22'), value: 200.42},
    {date: new Date('2010-02-23'), value: 197.06},
    {date: new Date('2010-02-24'), value: 200.66},
    {date: new Date('2010-02-25'), value: 202.00},
    {date: new Date('2010-02-26'), value: 204.62},
    {date: new Date('2010-03-01'), value: 208.99},
    {date: new Date('2010-03-02'), value: 208.85},
    {date: new Date('2010-03-03'), value: 209.33},
    {date: new Date('2010-03-04'), value: 210.71},
    {date: new Date('2010-03-05'), value: 218.95},
    {date: new Date('2010-03-08'), value: 219.08},
    {date: new Date('2010-03-09'), value: 223.02},
    {date: new Date('2010-03-10'), value: 224.84},
    {date: new Date('2010-03-11'), value: 225.50},
    {date: new Date('2010-03-12'), value: 226.60},
    {date: new Date('2010-03-15'), value: 223.84},
    {date: new Date('2010-03-16'), value: 224.45},
    {date: new Date('2010-03-17'), value: 224.12},
    {date: new Date('2010-03-18'), value: 224.65},
    {date: new Date('2010-03-19'), value: 222.25},
    {date: new Date('2010-03-22'), value: 224.75},
    {date: new Date('2010-03-23'), value: 228.36},
    {date: new Date('2010-03-24'), value: 229.37},
    {date: new Date('2010-03-25'), value: 226.65},
    {date: new Date('2010-03-26'), value: 230.90},
    {date: new Date('2010-03-29'), value: 232.39},
    {date: new Date('2010-03-30'), value: 235.84},
    {date: new Date('2010-03-31'), value: 235.00},
    {date: new Date('2010-04-01'), value: 235.97},
    {date: new Date('2010-04-02'), value: 235.97},
    {date: new Date('2010-04-05'), value: 238.49},
    {date: new Date('2010-04-06'), value: 239.54},
    {date: new Date('2010-04-07'), value: 240.60},
];

@Component({
  selector: 'app-history-graph',
  encapsulation: ViewEncapsulation.None,
  templateUrl: './history-graph.component.html',
  styleUrls: ['./history-graph.component.css']
})
export class HistoryGraphComponent implements OnInit {
  @Input() viewForm: FormGroup;

  title = 'Line Chart';

  private margin = {top: 20, right: 20, bottom: 30, left: 50};
  private width: number;
  private height: number;
  private x: any;
  private y: any;
  private svg: any;
  private line: d3Shape.Line<[number, number]>;

  constructor() {
    this.width = 900 - this.margin.left - this.margin.right;
    this.height = 500 - this.margin.top - this.margin.bottom;
  }

  ngOnInit() {
    this.initSvg();
    this.initAxis();
    this.drawAxis();
    this.drawLine();
  }

  private initSvg() {
    this.svg = d3.select('svg')
      .append('g')
      .attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');
  }

  private initAxis() {
    this.x = d3Scale.scaleTime().range([0, this.width]);
    this.y = d3Scale.scaleLinear().range([this.height, 0]);
    this.x.domain(d3Array.extent(STOCKS, (d) => d.date ));
    this.y.domain(d3Array.extent(STOCKS, (d) => d.value ));
  }

  private drawAxis() {

    this.svg.append('g')
      .attr('class', 'axis axis--x')
      .attr('transform', 'translate(0,' + this.height + ')')
      .call(d3Axis.axisBottom(this.x));

    this.svg.append('g')
      .attr('class', 'axis axis--y')
      .call(d3Axis.axisLeft(this.y))
      .append('text')
      .attr('class', 'axis-title')
      .attr('transform', 'rotate(-90)')
      .attr('y', 6)
      .attr('dy', '.71em')
      .style('text-anchor', 'end')
      .text('Price ($)');
  }

  private drawLine() {
    this.line = d3Shape.line()
      .x( (d: any) => this.x(d.date) )
      .y( (d: any) => this.y(d.value) );

    this.svg.append('path')
      .datum(STOCKS)
      .attr('class', 'line')
      .attr('d', this.line);
  }
}

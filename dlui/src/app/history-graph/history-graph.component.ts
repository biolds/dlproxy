import { Component, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { FormGroup } from '@angular/forms';

import * as d3 from 'd3-selection';
import * as d3Scale from 'd3-scale';
import * as d3ScaleChromatic from 'd3-scale-chromatic';
import * as d3Drag from 'd3-drag';
import * as d3Shape from 'd3-shape';
import * as d3Array from 'd3-array';
import * as d3Axis from 'd3-axis';
import * as d3Force from 'd3-force';

const data = {
  "nodes": [
    {"id": "Napoleon", "group": 1},
    {"id": "CountessdeLo", "group": 1},
    {"id": "Champtercier", "group": 1},
    {"id": "Cravatte", "group": 1},
    {"id": "Count", "group": 1},
    {"id": "Cosette", "group": 5},
    {"id": "Champmathieu", "group": 2},
    {"id": "Chenildieu", "group": 2},
    {"id": "Cochepaille", "group": 2},
    {"id": "Combeferre", "group": 8},
    {"id": "Courfeyrac", "group": 8},
    {"id": "Claquesous", "group": 4},
    {"id": "Child1", "group": 10},
    {"id": "Child2", "group": 10},
  ],
  "links": [
    {"source": "Chenildieu", "target": "Champmathieu", "value": 2},
    {"source": "Cochepaille", "target": "Champmathieu", "value": 2},
    {"source": "Cochepaille", "target": "Chenildieu", "value": 2},
    {"source": "Courfeyrac", "target": "Combeferre", "value": 13},
    {"source": "Child2", "target": "Child1", "value": 3},
  ]
};

const width = 600;
const height = 400;

function color() {
  const scale = d3Scale.scaleOrdinal(d3ScaleChromatic.schemeCategory10);
  return d => scale(d.group);
}

function drag(simulation) {
   function dragstarted(d) {
     if (!d3.event.active) simulation.alphaTarget(0.3).restart();
     d.fx = d.x;
     d.fy = d.y;
   }
 
   function dragged(d) {
     d.fx = d3.event.x;
     d.fy = d3.event.y;
   }
 
   function dragended(d) {
     if (!d3.event.active) simulation.alphaTarget(0);
     d.fx = null;
     d.fy = null;
   }
 
   return d3Drag.drag()
       .on("start", dragstarted)
       .on("drag", dragged)
       .on("end", dragended);
}

@Component({
  selector: 'app-history-graph',
  encapsulation: ViewEncapsulation.None,
  templateUrl: './history-graph.component.html',
  styleUrls: ['./history-graph.component.css']
})
export class HistoryGraphComponent implements OnInit {
  @Input() viewForm: FormGroup;
  private d3Node: any;
  private d3Link: any;
  private nodes: any;
  private links: any;
  private svg: any;
  private simulation: any;

  constructor() {
  }

  addNodes() {
    const nodes = [...this.nodes, {"id": "Dlproxy", "group": 3}];
    this.svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .enter()
        .append("circle")
          .attr("stroke", "#fff")
          .attr("stroke-width", 1.5)
          .attr("r", 5)
          .attr("fill", color())
          .call(drag(this.simulation));

    //this.simulation.start();
  }

  ngOnInit() {
    this.links = data.links.map(d => Object.create(d));
    this.nodes = data.nodes.map(d => Object.create(d));

    this.simulation = d3Force.forceSimulation(this.nodes)
        .force("link", d3Force.forceLink(this.links).id((d: any) => d.id))
        .force("charge", d3Force.forceManyBody())
        .force("center", d3Force.forceCenter(width / 2, height / 2));

    this.svg = d3.select("#d3-graph")
        .attr("viewBox", `0 0 ${width} ${height}`);

    this.d3Link = this.svg.append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(this.links)
      .join("line")
        .attr("stroke-width", (d: any) => Math.sqrt(d.value));

    this.d3Node = this.svg.append("g")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(this.nodes)
      .join("circle")
        .attr("r", 5)
        .attr("fill", color())
        .call(drag(this.simulation));

    this.d3Node.append("title")
        .text(d => d.id);

    this.simulation.on("tick", () => {
      this.d3Link
          .attr("x1", (d: any) => d.source.x)
          .attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x)
          .attr("y2", (d: any) => d.target.y);

      this.d3Node
          .attr("cx", (d: any) => d.x)
          .attr("cy", (d: any) => d.y);
    });

    setTimeout(() => this.addNodes(), 1000);
  }
}

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
  private color: any;
  private simulation: any;
  private nodesGroup: any;
  private linksGroup: any;
  newNodeNo = 1;

  constructor() {
  }

  restart() {
    // Apply the general update pattern to the nodes.
    this.d3Node = this.d3Node.data(this.nodes, (d: any) => { return d.id;});
    this.d3Node.exit().remove();
    let newNodes = this.d3Node.enter().append("g").attr('class', 'node');
    newNodes.append('circle')
      .attr("fill", (d: any) => { return this.color(d.id); })
      .attr("r", 8);
    newNodes.append('text')
      .attr('x', 11)
      .attr('y', 5)
      .text(function(d: any) { return d.title; });

    this.d3Node = newNodes.call(drag(this.simulation))
      .merge(this.d3Node);

    // Apply the general update pattern to the links.
    this.d3Link = this.d3Link.data(this.links, (d: any) => { return d.source.id + "-" + d.target.id; });
    this.d3Link.exit().remove();
    this.d3Link = this.d3Link.enter().append("line")
        .attr('class', 'link')
        .merge(this.d3Link);

    // Update and restart the simulation.
    this.simulation.nodes(this.nodes);
    this.simulation.force("link").links(this.links);
    this.simulation.alpha(1).restart();
  }

  ngOnInit() {
    var svg = d3.select("#d3-graph"),
        width = +svg.attr("width"),
        height = +svg.attr("height");
    this.color = d3Scale.scaleOrdinal(d3ScaleChromatic.schemeCategory10);

    var a = {id: "a", title: "title A"},
        b = {id: "b", title: "title B"},
        c = {id: "c", title: "title C"};
    this.nodes = [a, b, c];
    this.links = [];

    this.simulation = d3Force.forceSimulation(this.nodes)
        .force("charge", d3Force.forceManyBody().strength(-1000))
        .force("link", d3Force.forceLink(this.links).distance(200))
        .force("x", d3Force.forceX())
        .force("y", d3Force.forceY())
        .alphaTarget(1)
        .on("tick", () => {
          this.d3Node.attr("transform", function(d: any) {
            return "translate(" + d.x + "," + d.y + ")";
          })

      	  this.d3Link.attr("x1", function(d: any) { return d.source.x; })
      	      .attr("y1", function(d: any) { return d.source.y; })
      	      .attr("x2", function(d: any) { return d.target.x; })
      	      .attr("y2", function(d: any) { return d.target.y; });
	});

    var g = svg.append("g").attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
    this.d3Link = g.append("g").attr("stroke", "#000").attr("stroke-width", 1.5).selectAll(".link");
    this.d3Node = g.append("g")/*.attr("stroke", "#fff").attr("stroke-width", 1.5)*/.selectAll(".node");

    this.restart();

    setTimeout(() => {
      this.links.push({source: a, target: b}); // Add a-b.
      this.links.push({source: b, target: c}); // Add b-c.
      this.links.push({source: c, target: a}); // Add c-a.
      this.restart();
    }, 1000);

    setTimeout(() => {
      this.nodes.pop(); // Remove c.
      this.links.pop(); // Remove c-a.
      this.links.pop(); // Remove b-c.
      this.restart();
    }, 2000);

    setTimeout(() => {
      this.nodes.push(c); // Re-add c.
      this.links.push({source: b, target: c}); // Re-add b-c.
      this.links.push({source: c, target: a}); // Re-add c-a.
      this.restart();
    }, 3000);

  }
}

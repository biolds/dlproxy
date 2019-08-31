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
  private svg: any;
  private simulation: any;
  private drag: any;
  private nodesGroup: any;
  private linksGroup: any;
  newNodeNo = 1;

  constructor() {
  }

  ngOnInit() {
    var svg = d3.select("#d3-graph"),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        color = d3Scale.scaleOrdinal(d3ScaleChromatic.schemeCategory10);
    
    var a = {id: "a"},
        b = {id: "b"},
        c = {id: "c"},
        nodes = [a, b, c],
        links = [];
    
    var simulation = d3Force.forceSimulation(<any>nodes)
        .force("charge", d3Force.forceManyBody().strength(-1000))
        .force("link", d3Force.forceLink(links).distance(200))
        .force("x", d3Force.forceX())
        .force("y", d3Force.forceY())
        .alphaTarget(1)
        .on("tick", ticked);
    
    var g = svg.append("g").attr("transform", "translate(" + width / 2 + "," + height / 2 + ")"),
        link = g.append("g").attr("stroke", "#000").attr("stroke-width", 1.5).selectAll(".link"),
        node = g.append("g").attr("stroke", "#fff").attr("stroke-width", 1.5).selectAll(".node");
    
    restart();
    
    setTimeout(function() {
      links.push({source: a, target: b}); // Add a-b.
      links.push({source: b, target: c}); // Add b-c.
      links.push({source: c, target: a}); // Add c-a.
      restart();
    }, 1000);
    
    setTimeout(function() {
      nodes.pop(); // Remove c.
      links.pop(); // Remove c-a.
      links.pop(); // Remove b-c.
      restart();
    }, 2000);
    
    setTimeout(function() {
      nodes.push(c); // Re-add c.
      links.push({source: b, target: c}); // Re-add b-c.
      links.push({source: c, target: a}); // Re-add c-a.
      restart();
    }, 3000);
    
    function restart() {
    
      // Apply the general update pattern to the nodes.
      node = node.data(<any>nodes, function(d) { return d.id;});
      node.exit().remove();
      //node = node.enter().append("circle").attr("fill", function(d) { return color(d.id); }).attr("r", 8).merge(node);
      node = node.enter().append("circle")
        .attr("fill", function(d) { return color(d.id); }).attr("r", 8).call(drag(simulation))
        .merge(node);
    
      // Apply the general update pattern to the links.
      link = link.data(links, function(d) { return d.source.id + "-" + d.target.id; });
      link.exit().remove();
      link = link.enter().append("line").merge(link);
    
      // Update and restart the simulation.
      simulation.nodes(nodes);
      simulation.force("link").links(links);
      simulation.alpha(1).restart();
    }
    
    function ticked() {
      node.attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; })
    
      link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });
    }
  }
}

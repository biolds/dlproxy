import { Component, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { FormGroup } from '@angular/forms';

import { ObjList } from '../objlist';
import { UrlAccess } from '../url-access';

import * as d3 from 'd3-selection';
import * as d3Scale from 'd3-scale';
import * as d3ScaleChromatic from 'd3-scale-chromatic';
import * as d3Drag from 'd3-drag';
import * as d3Shape from 'd3-shape';
import * as d3Array from 'd3-array';
import * as d3Axis from 'd3-axis';
import * as d3Force from 'd3-force';

import { UrlService } from '../url.service';


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
  urlsMap = {};
  linksMap = {};
  domainsMap = {};
  urls: UrlAccess[];
  newNodeNo = 1;
  interval: number;

  constructor(private urlService: UrlService) {
  }

  getUrls() {
    let startDate = this.viewForm.value.startDate.hours(0).minutes(0).seconds(0).unix();
    let endDate = this.viewForm.value.endDate.hours(0).minutes(0).seconds(0).unix();
    endDate += 60 * 60 * 24;

    let filter = `f_date__gte=${startDate}&f_date__lt=${endDate}`;

    if (this.viewForm.value.mimeFilter === 'webpages') {
      filter += '&f_url__mimetype=text/html&f_url__is_ajax=false';
    }

    if (this.viewForm.value.search) {
      filter += `&q=${this.viewForm.value.search}`;
    }

    if (this.viewForm.value.httpStatus !== 'all') {
      let s = this.viewForm.value.httpStatus;
      s = parseInt(s, 10);
      if (this.viewForm.value.mimeFilter === 'webpages' && s === 2) {
        filter += `&f_status=200`;
      } else {
        filter += `&f_status__gte=${s}00&f_status__lt=${s + 1}00`;
      }
    }

    const searchTerms = this.viewForm.value.search.split(' ').filter(s => s !== '').map(s => s.toLowerCase());
    this.urlService.getUrlAccesses(0, 1000, filter).subscribe((urls) => {
      const nodesLength = this.nodes.length;
      const linksLength = this.links.length;

      let urlsMap = {};
      let linksMap = {};

      urls.objs.map((url) => {
        console.log('got url', url.url);
        let dst = url.url.id;
        if (!urlsMap[dst]) {
          if (this.urlsMap[dst] === undefined) {
            urlsMap[dst] = {id: dst, title: url.url.url, url: url.url.url};
            this.nodes.push(urlsMap[dst]);
            console.log('addding node', dst);
          } else {
            urlsMap[dst] = this.urlsMap[dst];
            console.log('node already there', dst);
          }
        }

        if (url.url.title) {
          urlsMap[dst].title = url.url.title;
        }

        if (url.referer) {
          let src = url.referer.id;

          if (!urlsMap[src]) {
            if (this.urlsMap[src] === undefined) {
              urlsMap[src] = {id: src, title: url.referer.url, url: url.referer.url};
              this.nodes.push(urlsMap[src]);
              console.log('addding node', src);
            } else {
              urlsMap[src] = this.urlsMap[src];
              console.log('node already there', src);
            }
          }

          let srcNode = urlsMap[src];
          let dstNode = urlsMap[dst];

          if (!linksMap[src]) {
            linksMap[src] = {};
          }

          if (!linksMap[src] || !linksMap[src][dst]) {
            if (!this.linksMap[src] || !this.linksMap[src][dst]) {
              let link = {source: srcNode, target: dstNode};
              linksMap[src][dst] = link;
              console.log('adding link', src, dst);
              this.links.push(link);
            } else {
              linksMap[src][dst] = this.linksMap[src][dst];
              console.log('link already exist', src, dst);
            }
          }
        }
      });

      let gotChange = (this.nodes.length !== nodesLength) || (this.links.length !== linksLength);

      // remove deleted elements
      let newNodes = [];
      this.nodes.slice(0, nodesLength).map((url, i) => {
        if (urlsMap[url.id]) {
          newNodes.push(url);
        } else {
          gotChange = true;
        }
      });
      this.nodes = newNodes.concat(this.nodes.slice(nodesLength));

      let newLinks = [];
      this.links.slice(0, linksLength).map((link, i) => {
        if (linksMap[link.source.id] && linksMap[link.source.id][link.target.id]) {
          newLinks.push(link);
        } else {
          gotChange = true;
        }
      });
      this.links = newLinks.concat(this.links.slice(linksLength));

      this.urlsMap = urlsMap;
      this.linksMap = linksMap;

      if (gotChange) {
        this.restart();
        console.log('restared');
      } else {
        console.log('no change');
      }
    });
  }

  refreshUrls() {
    this.getUrls();
  }

  restart() {
    console.log('current', this.nodes);
    // Apply the general update pattern to the nodes.
    this.d3Node = this.d3Node.data(this.nodes, (d: any) => { return d.id;});
    this.d3Node.exit().remove();
    let newNodes = this.d3Node.enter().append("g").attr('class', 'node');
    newNodes.append('circle')
      .attr("fill", (d: any) => { return this.color(d.id); })
      .attr("r", 8)
      .on('mouseover', function(d){
          console.log('mouse over', this, d);
          d3.select('#d3-graph').selectAll('.node > text').attr('class', '');
          d3.select(this.parentNode).selectAll('text').attr('class', 'hovered');
      });
    newNodes.append('text')
      .attr('x', 11)
      .attr('y', 5)
      .text(function(d: any) { return d.title; })

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
    var width = 1600;
    var height = 800;
    var svg = d3.select("#d3-graph")
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", `0 0 ${width} ${height}`);
    this.color = d3Scale.scaleOrdinal(d3ScaleChromatic.schemeCategory10);

    this.nodes = [];
    this.links = [];

    this.simulation = d3Force.forceSimulation(this.nodes)
        .force("charge", d3Force.forceManyBody().strength(-300))
        .force("link", d3Force.forceLink(this.links).distance(60))
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

    var g = svg.append("g")
        .attr("transform", `translate(${width / 2},${height / 2})`)
        .attr("width", width)
        .attr("height", height);

    this.d3Link = g.append("g").attr("stroke", "#000").attr("stroke-width", 1.5).selectAll(".link");
    this.d3Node = g.append("g").selectAll(".node");

    this.getUrls();
    this.restart();

    this.interval = setInterval(() => {
      this.refreshUrls();
    }, 5000);
  }
}

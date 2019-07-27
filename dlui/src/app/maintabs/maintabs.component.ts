import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-maintabs',
  templateUrl: './maintabs.component.html',
  styleUrls: ['./maintabs.component.css']
})
export class MaintabsComponent implements OnInit {
  navLinks: any[];

  constructor(private router: Router) {
    this.navLinks = [
        {
            label: 'History',
            path: '/'
        }, {
            label: 'Downloads',
            path: '/downloads'
        }, {
            label: 'Settings',
            path: '/settings'
        }
    ];
  }

  ngOnInit() {
  }
}

import { NgModule } from '@angular/core';
import { Routes, RouterModule, UrlSegment } from '@angular/router';
import { DownloadComponent } from './download/download.component';
import { DownloadsComponent } from './downloads/downloads.component';
import { HistoryComponent } from './history/history.component';
import { ErrorComponent } from './error/error.component';
import { MaintabsComponent } from './maintabs/maintabs.component';
import { SettingsComponent } from './settings/settings.component';

declare var myAddress: string;

export function otherHostMatcher(url: UrlSegment[]) {
  const addrLength: number = window.location.href.length - window.location.pathname.length;
  const currentAddr: string = window.location.href.substr(0, addrLength + 1);

  if (currentAddr === myAddress) {
    return null;
  }

  return { consumed: url };
}

export function downloadMatcher(url: UrlSegment[]) {
  //console.log('got url:', url);

  if (url.length < 3 || url[0].path !== 'download') {
    return null;
  }

  return {
    consumed: url,
    posParams: {
      url: url.slice(1)
    }
  };
}

const routes: Routes = [
  { matcher: otherHostMatcher, component: ErrorComponent },
  { path: 'download/:id', component: DownloadComponent, },
  { path: '', component: MaintabsComponent,
    children: [
      { path: 'downloads', component: DownloadsComponent },
      { path: 'settings', component: SettingsComponent },
      { path: '', component: HistoryComponent }
    ]
  },
  { path: '**', component: ErrorComponent, },
  // { matcher: downloadMatcher, component: DownloadComponent, }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

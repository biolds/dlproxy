import { NgModule } from '@angular/core';
import { Routes, RouterModule, UrlSegment } from '@angular/router';
import { DownloadComponent } from './download/download.component';
import { ErrorComponent } from './error/error.component';
//import { myAddress } from './global'

declare var myAddress: string;

export function otherHostMatcher(url: UrlSegment[]) {
  console.log('myaddress', myAddress);
  console.log('wind', window.location.href);

  const addrLength: number = window.location.href.length - window.location.pathname.length;
  const currentAddr: string = window.location.href.substr(0, addrLength + 1);

  console.log('curr', currentAddr);
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
  // { matcher: downloadMatcher, component: DownloadComponent, }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

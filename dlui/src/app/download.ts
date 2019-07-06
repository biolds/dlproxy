import { Url } from './url';

export class Download {
  id: number;
  url: Url;
  data: string;
  filesize: number;
  state: string;
}

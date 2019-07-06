import { Url } from './url';

export class Download {
  id: number;
  url: Url;
  date: string;
  filesize: number;
  current_size: number;
  state: string;
}

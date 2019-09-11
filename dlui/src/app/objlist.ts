export class ObjList<T> {
  count: number;
  offset: number;
  objs: T[];
}

export class ObjListWithDates<T> extends ObjList<T> {
  date_min: number;
  date_max: number;
}

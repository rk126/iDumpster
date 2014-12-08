/**
 * @jsx React.DOM
 */
var Truck = React.createClass({
  render: function() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.location.x}, {this.props.location.y}</td>
        <td>{this.props.status}</td>
        <td>{this.props.fuel}</td>
        <td>{this.props.trash}</td>
      </tr>
    );
  }
});

var TruckTable = React.createClass({
  loadStatusFromServer: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadStatusFromServer();
    setInterval(this.loadStatusFromServer, this.props.pollInterval);
  },
  render: function() {
    var truckNodes = this.state.data.map(function(truck, index) {
      return (
        <Truck name={truck.name} location={truck.location} status={truck.status} fuel={truck.fuel_level} trash={truck.trash_level} key={index} />
      );
    });
    return (
      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th className="col-md-1">Truck Name</th>
              <th className="col-md-1">Location</th>
              <th className="col-md-1">Status</th>
              <th className="col-md-1">Fuel Level</th>
              <th className="col-md-1">Trash Level</th>
            </tr>
          </thead>
          <tbody>
            {truckNodes}
          </tbody>
        </table>
      </div>
    );
  }
});

React.renderComponent(
  <TruckTable url="trucks.json" pollInterval={1000} />,
  document.getElementById('trucks')
);
